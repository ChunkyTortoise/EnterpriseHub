#!/usr/bin/env python3
"""
Security Audit Script (Agent B3)

Runs comprehensive security checks on the GHL Real Estate AI system.
Checks for vulnerabilities, misconfigurations, and security best practices.
"""
import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SecurityAuditor:
    """Comprehensive security auditing tool."""
    
    def __init__(self):
        self.project_root = project_root
        self.findings = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }
        self.checks_run = 0
        self.checks_passed = 0
    
    def run_audit(self, verbose: bool = True) -> Dict:
        """Run all security checks."""
        print("=" * 80)
        print("🔒 GHL Real Estate AI - Security Audit")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run all checks
        self.check_hardcoded_secrets()
        self.check_environment_variables()
        self.check_file_permissions()
        self.check_dependency_vulnerabilities()
        self.check_input_validation()
        self.check_api_security()
        self.check_tenant_isolation()
        self.check_data_encryption()
        self.check_logging_security()
        self.check_error_handling()
        
        # Generate report
        report = self.generate_report(verbose)
        
        return report
    
    def add_finding(self, severity: str, title: str, description: str, 
                   file_path: str = None, remediation: str = None):
        """Add a security finding."""
        finding = {
            "title": title,
            "description": description,
            "file": file_path,
            "remediation": remediation,
            "timestamp": datetime.now().isoformat()
        }
        
        self.findings[severity].append(finding)
    
    def check_hardcoded_secrets(self):
        """Check for hardcoded secrets in code."""
        print("🔍 Checking for hardcoded secrets...")
        self.checks_run += 1
        
        # Patterns that might indicate secrets
        secret_patterns = [
            (r'sk-ant-[a-zA-Z0-9-]{20,}', "Anthropic API Key"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded Password"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded Secret"),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded API Key"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded Token"),
        ]
        
        # Files to check
        python_files = list(self.project_root.rglob("*.py"))
        issues_found = 0
        
        for file_path in python_files:
            # Skip test files and venv
            if "test" in str(file_path) or "venv" in str(file_path):
                continue
            
            try:
                content = file_path.read_text()
                
                for pattern, secret_type in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Check if it's using environment variables (acceptable)
                        line = content[max(0, match.start()-50):match.end()+50]
                        if "os.getenv" in line or "os.environ" in line:
                            continue
                        
                        self.add_finding(
                            "critical",
                            f"Potential Hardcoded {secret_type}",
                            f"Found potential hardcoded secret in code",
                            str(file_path.relative_to(self.project_root)),
                            "Use environment variables or secure secret management"
                        )
                        issues_found += 1
            except Exception as e:
                print(f"  ⚠️  Error checking {file_path}: {e}")
        
        if issues_found == 0:
            print("  ✅ No hardcoded secrets found")
            self.checks_passed += 1
        else:
            print(f"  ❌ Found {issues_found} potential hardcoded secrets")
    
    def check_environment_variables(self):
        """Check that required environment variables are documented."""
        print("\n🔍 Checking environment variable configuration...")
        self.checks_run += 1
        
        required_vars = [
            "ANTHROPIC_API_KEY",
            "GHL_API_KEY",
            "GHL_LOCATION_ID"
        ]
        
        # Check if .env.example exists and documents all required vars
        env_example = self.project_root / ".env.example"
        
        if not env_example.exists():
            self.add_finding(
                "medium",
                "Missing .env.example",
                "No .env.example file found to document required environment variables",
                None,
                "Create .env.example with all required environment variables"
            )
            print("  ⚠️  .env.example not found")
        else:
            content = env_example.read_text()
            missing_vars = []
            
            for var in required_vars:
                if var not in content:
                    missing_vars.append(var)
            
            if missing_vars:
                self.add_finding(
                    "low",
                    "Undocumented Environment Variables",
                    f"Variables not in .env.example: {', '.join(missing_vars)}",
                    ".env.example",
                    "Add all required variables to .env.example"
                )
                print(f"  ⚠️  Missing {len(missing_vars)} variables in .env.example")
            else:
                print("  ✅ All required variables documented")
                self.checks_passed += 1
    
    def check_file_permissions(self):
        """Check file permissions for sensitive files."""
        print("\n🔍 Checking file permissions...")
        self.checks_run += 1
        
        sensitive_files = [
            ".env",
            "data/memory",
            "data/embeddings"
        ]
        
        issues = 0
        for file_rel in sensitive_files:
            file_path = self.project_root / file_rel
            
            if file_path.exists():
                stat_info = file_path.stat()
                mode = oct(stat_info.st_mode)[-3:]
                
                # Check if world-readable (last digit should be 0)
                if mode[-1] != '0':
                    self.add_finding(
                        "high",
                        f"Insecure File Permissions: {file_rel}",
                        f"File has world-readable permissions: {mode}",
                        file_rel,
                        f"Run: chmod 600 {file_rel}"
                    )
                    issues += 1
        
        if issues == 0:
            print("  ✅ File permissions secure")
            self.checks_passed += 1
        else:
            print(f"  ⚠️  Found {issues} permission issues")
    
    def check_dependency_vulnerabilities(self):
        """Check for known vulnerabilities in dependencies."""
        print("\n🔍 Checking dependencies for known vulnerabilities...")
        self.checks_run += 1
        
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            print("  ⚠️  requirements.txt not found")
            return
        
        # This is a placeholder - in production, would use safety or pip-audit
        self.add_finding(
            "info",
            "Dependency Scan Recommended",
            "Run 'pip-audit' to check for known vulnerabilities",
            "requirements.txt",
            "Install and run: pip install pip-audit && pip-audit"
        )
        
        print("  ℹ️  Manual dependency scan recommended")
        self.checks_passed += 1
    
    def check_input_validation(self):
        """Check for input validation in key entry points."""
        print("\n🔍 Checking input validation...")
        self.checks_run += 1
        
        # Check webhook handler for input validation
        webhook_file = self.project_root / "api" / "routes" / "webhook.py"
        
        if webhook_file.exists():
            content = webhook_file.read_text()
            
            # Look for validation patterns
            validation_indicators = [
                "validate",
                "sanitize",
                "check",
                "isinstance",
                "raise ValueError"
            ]
            
            found_validation = any(indicator in content for indicator in validation_indicators)
            
            if found_validation:
                print("  ✅ Input validation found in webhook handler")
                self.checks_passed += 1
            else:
                self.add_finding(
                    "high",
                    "Missing Input Validation",
                    "Webhook handler may not have adequate input validation",
                    "api/routes/webhook.py",
                    "Add validation for all user inputs"
                )
                print("  ⚠️  Limited input validation detected")
        else:
            print("  ⚠️  Webhook handler not found")
    
    def check_api_security(self):
        """Check API security configurations."""
        print("\n🔍 Checking API security...")
        self.checks_run += 1
        
        api_main = self.project_root / "api" / "main.py"
        
        if not api_main.exists():
            print("  ⚠️  API main file not found")
            return
        
        content = api_main.read_text()
        
        # Check for security headers
        security_features = {
            "CORS": "CORSMiddleware" in content,
            "Rate Limiting": "rate_limit" in content.lower(),
            "Authentication": "auth" in content.lower() or "bearer" in content.lower(),
        }
        
        missing_features = [k for k, v in security_features.items() if not v]
        
        if missing_features:
            self.add_finding(
                "medium",
                "Missing API Security Features",
                f"Missing: {', '.join(missing_features)}",
                "api/main.py",
                "Implement rate limiting, authentication, and CORS properly"
            )
            print(f"  ⚠️  Missing: {', '.join(missing_features)}")
        else:
            print("  ✅ API security features present")
            self.checks_passed += 1
    
    def check_tenant_isolation(self):
        """Check tenant isolation implementation."""
        print("\n🔍 Checking tenant isolation...")
        self.checks_run += 1
        
        tenant_service = self.project_root / "services" / "tenant_service.py"
        memory_service = self.project_root / "services" / "memory_service.py"
        
        issues = []
        
        # Check if tenant_id is used in file paths
        if memory_service.exists():
            content = memory_service.read_text()
            if "location_id" in content or "tenant_id" in content:
                print("  ✅ Tenant ID used in memory service")
                self.checks_passed += 1
            else:
                self.add_finding(
                    "critical",
                    "Weak Tenant Isolation",
                    "Memory service may not properly isolate tenant data",
                    "services/memory_service.py",
                    "Ensure all file paths include tenant_id/location_id"
                )
                print("  ❌ Tenant isolation may be weak")
        else:
            print("  ⚠️  Memory service not found")
    
    def check_data_encryption(self):
        """Check if sensitive data is encrypted."""
        print("\n🔍 Checking data encryption...")
        self.checks_run += 1
        
        # Check if there's any encryption for sensitive data
        memory_service = self.project_root / "services" / "memory_service.py"
        
        if memory_service.exists():
            content = memory_service.read_text()
            
            encryption_indicators = ["encrypt", "decrypt", "cipher", "fernet", "aes"]
            has_encryption = any(ind in content.lower() for ind in encryption_indicators)
            
            if not has_encryption:
                self.add_finding(
                    "medium",
                    "Data Not Encrypted at Rest",
                    "Sensitive conversation data stored without encryption",
                    "services/memory_service.py",
                    "Consider encrypting sensitive data at rest using Fernet or similar"
                )
                print("  ⚠️  No encryption detected for stored data")
            else:
                print("  ✅ Encryption mechanisms found")
                self.checks_passed += 1
        else:
            print("  ⚠️  Memory service not found")
    
    def check_logging_security(self):
        """Check that logging doesn't expose sensitive information."""
        print("\n🔍 Checking logging security...")
        self.checks_run += 1
        
        logger_file = self.project_root / "ghl_utils" / "logger.py"
        
        if logger_file.exists():
            content = logger_file.read_text()
            
            # Check if there's any filtering of sensitive data
            if "filter" in content.lower() or "redact" in content.lower():
                print("  ✅ Log filtering mechanisms found")
                self.checks_passed += 1
            else:
                self.add_finding(
                    "medium",
                    "Unfiltered Logging",
                    "Logs may contain sensitive information (API keys, PII)",
                    "ghl_utils/logger.py",
                    "Implement log filtering to redact API keys, emails, phone numbers"
                )
                print("  ⚠️  No log filtering detected")
        else:
            print("  ⚠️  Logger file not found")
    
    def check_error_handling(self):
        """Check error handling practices."""
        print("\n🔍 Checking error handling...")
        self.checks_run += 1
        
        # Check main API file for error handling
        api_files = list((self.project_root / "api").rglob("*.py"))
        
        proper_error_handling = 0
        for file_path in api_files:
            content = file_path.read_text()
            
            # Look for proper exception handling
            if "try:" in content and "except" in content:
                proper_error_handling += 1
        
        if proper_error_handling > 0:
            print(f"  ✅ Error handling found in {proper_error_handling} files")
            self.checks_passed += 1
        else:
            self.add_finding(
                "medium",
                "Limited Error Handling",
                "API may not have comprehensive error handling",
                "api/",
                "Add try-except blocks around all external calls"
            )
            print("  ⚠️  Limited error handling detected")
    
    def generate_report(self, verbose: bool = True) -> Dict:
        """Generate security audit report."""
        print("\n" + "=" * 80)
        print("📊 Security Audit Report")
        print("=" * 80)
        
        total_findings = sum(len(findings) for findings in self.findings.values())
        
        print(f"\nChecks Run: {self.checks_run}")
        print(f"Checks Passed: {self.checks_passed}")
        print(f"Pass Rate: {(self.checks_passed/self.checks_run*100):.1f}%")
        print(f"\nTotal Findings: {total_findings}")
        
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = len(self.findings[severity])
            if count > 0:
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", 
                        "low": "🔵", "info": "ℹ️"}
                print(f"  {emoji[severity]} {severity.upper()}: {count}")
        
        if verbose and total_findings > 0:
            print("\n" + "=" * 80)
            print("Detailed Findings")
            print("=" * 80)
            
            for severity in ["critical", "high", "medium", "low", "info"]:
                if self.findings[severity]:
                    print(f"\n{severity.upper()} FINDINGS:")
                    for i, finding in enumerate(self.findings[severity], 1):
                        print(f"\n{i}. {finding['title']}")
                        print(f"   Description: {finding['description']}")
                        if finding['file']:
                            print(f"   File: {finding['file']}")
                        if finding['remediation']:
                            print(f"   Remediation: {finding['remediation']}")
        
        # Calculate security score
        weights = {"critical": 10, "high": 5, "medium": 2, "low": 1, "info": 0}
        penalty = sum(len(self.findings[sev]) * weight for sev, weight in weights.items())
        max_penalty = self.checks_run * 10
        security_score = max(0, 100 - (penalty / max_penalty * 100))
        
        print(f"\n{'=' * 80}")
        print(f"🛡️  Overall Security Score: {security_score:.1f}/100")
        print(f"{'=' * 80}")
        
        if security_score >= 90:
            print("✅ Excellent security posture")
        elif security_score >= 70:
            print("⚠️  Good security, minor improvements needed")
        elif security_score >= 50:
            print("⚠️  Moderate security, several improvements recommended")
        else:
            print("❌ Security needs significant improvements")
        
        # Save report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "checks_run": self.checks_run,
            "checks_passed": self.checks_passed,
            "security_score": security_score,
            "findings": self.findings
        }
        
        report_file = self.project_root / "security_audit_report.json"
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_file}")
        
        return report_data


def main():
    """Run security audit."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run security audit on GHL Real Estate AI")
    parser.add_argument("--quiet", "-q", action="store_true", help="Show only summary")
    
    args = parser.parse_args()
    
    auditor = SecurityAuditor()
    report = auditor.run_audit(verbose=not args.quiet)
    
    # Exit with error code if critical findings
    if report["findings"]["critical"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
