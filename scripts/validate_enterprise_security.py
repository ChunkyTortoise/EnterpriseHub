#!/usr/bin/env python3
"""
Enterprise Security Validation Script
Comprehensive security assessment for Jorge's Revenue Acceleration Platform

VALIDATION AREAS:
1. Authentication & Authorization
2. Data Protection & Privacy
3. API Security Hardening
4. Infrastructure Security
5. Compliance & Auditing
"""

import asyncio
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SecurityValidator:
    """Comprehensive enterprise security validation."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.findings: Dict[str, List[Dict[str, Any]]] = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }
        self.passed_checks = 0
        self.total_checks = 0

    def log_finding(self, severity: str, category: str, title: str,
                   description: str, remediation: str = None,
                   compliance_impact: List[str] = None):
        """Log a security finding."""
        finding = {
            "category": category,
            "title": title,
            "description": description,
            "remediation": remediation,
            "compliance_impact": compliance_impact or [],
            "timestamp": datetime.utcnow().isoformat()
        }
        self.findings[severity].append(finding)

    def print_section(self, title: str):
        """Print section header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

    def print_check(self, check_name: str, passed: bool, details: str = ""):
        """Print individual check result."""
        self.total_checks += 1
        if passed:
            self.passed_checks += 1
            status = f"{Colors.OKGREEN}✓ PASS{Colors.ENDC}"
        else:
            status = f"{Colors.FAIL}✗ FAIL{Colors.ENDC}"

        print(f"{status} {check_name}")
        if details:
            print(f"       {Colors.OKCYAN}{details}{Colors.ENDC}")

    # ========================================================================
    # 1. Authentication & Authorization Validation
    # ========================================================================

    def validate_authentication(self):
        """Validate authentication and authorization controls."""
        self.print_section("1. AUTHENTICATION & AUTHORIZATION")

        # Check 1.1: JWT Secret Key Strength
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            self.print_check(
                "JWT Secret Key Configuration",
                False,
                "JWT_SECRET_KEY not set in environment"
            )
            self.log_finding(
                "critical",
                "Authentication",
                "Missing JWT Secret Key",
                "JWT_SECRET_KEY environment variable is not configured",
                "Set a cryptographically secure JWT secret (minimum 64 characters)",
                ["OWASP A02:2021", "SOC2 CC6.1"]
            )
        elif len(jwt_secret) < 32:
            self.print_check(
                "JWT Secret Key Strength",
                False,
                f"Secret too short: {len(jwt_secret)} chars (minimum 32)"
            )
            self.log_finding(
                "high",
                "Authentication",
                "Weak JWT Secret Key",
                f"JWT secret is only {len(jwt_secret)} characters (minimum 32)",
                "Generate a new JWT secret with at least 64 characters",
                ["OWASP A02:2021"]
            )
        else:
            self.print_check(
                "JWT Secret Key Strength",
                True,
                f"Secret length: {len(jwt_secret)} chars"
            )

        # Check 1.2: Enhanced JWT Implementation
        jwt_auth_file = self.project_root / "ghl_real_estate_ai/api/middleware/enhanced_auth.py"
        if jwt_auth_file.exists():
            content = jwt_auth_file.read_text()

            # Check for rate limiting
            has_rate_limiting = "check_rate_limit" in content
            self.print_check(
                "JWT Rate Limiting",
                has_rate_limiting,
                "Rate limiting on authentication" if has_rate_limiting else ""
            )

            # Check for token blacklist
            has_blacklist = "blacklist_token" in content
            self.print_check(
                "JWT Token Blacklist",
                has_blacklist,
                "Token revocation mechanism" if has_blacklist else ""
            )

            # Check for proper token validation
            has_validation = "verify_token" in content and "aud" in content and "iss" in content
            self.print_check(
                "JWT Claims Validation",
                has_validation,
                "Audience and issuer validation" if has_validation else ""
            )
        else:
            self.print_check("Enhanced JWT Implementation", False, "File not found")
            self.log_finding(
                "high",
                "Authentication",
                "Missing Enhanced JWT Implementation",
                "enhanced_auth.py not found - may be using basic JWT only",
                "Implement enhanced JWT with rate limiting and blacklist"
            )

        # Check 1.3: Multi-tenant Isolation
        tenant_service_file = self.project_root / "ghl_real_estate_ai/services/tenant_service.py"
        if tenant_service_file.exists():
            content = tenant_service_file.read_text()
            has_isolation = "location_id" in content and "validate" in content.lower()
            self.print_check(
                "Multi-tenant Data Isolation",
                has_isolation,
                "Tenant validation implemented"
            )
        else:
            self.print_check("Multi-tenant Isolation", False, "Tenant service not found")

        # Check 1.4: Password Security
        auth_files = list((self.project_root / "ghl_real_estate_ai/api/middleware").glob("*auth*.py"))
        has_bcrypt = False
        for auth_file in auth_files:
            if "bcrypt" in auth_file.read_text():
                has_bcrypt = True
                break

        self.print_check(
            "Password Hashing Algorithm",
            has_bcrypt,
            "bcrypt password hashing" if has_bcrypt else "Weak or missing password hashing"
        )

        if not has_bcrypt:
            self.log_finding(
                "high",
                "Authentication",
                "Weak Password Hashing",
                "bcrypt password hashing not found in authentication modules",
                "Implement bcrypt with appropriate cost factor (12+)",
                ["OWASP A02:2021", "PCI DSS 8.2.1"]
            )

    # ========================================================================
    # 2. Data Protection & Privacy Validation
    # ========================================================================

    def validate_data_protection(self):
        """Validate data protection and privacy controls."""
        self.print_section("2. DATA PROTECTION & PRIVACY")

        # Check 2.1: Database Encryption Configuration
        env_template = self.project_root / ".env.jorge.template"
        if env_template.exists():
            content = env_template.read_text()
            has_db_ssl = "sslmode" in content.lower() or "ssl" in content.lower()
            self.print_check(
                "Database SSL/TLS Configuration",
                has_db_ssl,
                "SSL mode configured" if has_db_ssl else "No SSL configuration found"
            )

            if not has_db_ssl:
                self.log_finding(
                    "high",
                    "Data Protection",
                    "Database Connection Encryption Missing",
                    "Database connections may not be using SSL/TLS",
                    "Add ?sslmode=require to DATABASE_URL",
                    ["GDPR Article 32", "HIPAA 164.312(e)(1)"]
                )
        else:
            self.print_check("Database Configuration Check", False, "Template not found")

        # Check 2.2: Redis Security
        redis_config_found = False
        config_file = self.project_root / "ghl_real_estate_ai/ghl_utils/config.py"
        if config_file.exists():
            content = config_file.read_text()
            redis_config_found = "redis_url" in content.lower()
            has_redis_password = "redis_password" in content.lower() or "password" in content

            self.print_check(
                "Redis Authentication",
                has_redis_password,
                "Password authentication configured" if has_redis_password else ""
            )

            if not has_redis_password:
                self.log_finding(
                    "medium",
                    "Data Protection",
                    "Redis Authentication Missing",
                    "Redis may not have password authentication configured",
                    "Configure Redis with requirepass and use authenticated connection",
                    ["OWASP A01:2021"]
                )

        # Check 2.3: PII Field Encryption
        security_framework_file = self.project_root / "ghl_real_estate_ai/services/security_framework.py"
        if security_framework_file.exists():
            content = security_framework_file.read_text()
            has_sanitization = "sanitize_input" in content
            self.print_check(
                "Input Sanitization Framework",
                has_sanitization,
                "Input sanitization implemented"
            )
        else:
            self.print_check("Security Framework", False, "File not found")
            self.log_finding(
                "medium",
                "Data Protection",
                "Missing Security Framework",
                "security_framework.py not found",
                "Implement comprehensive security framework"
            )

        # Check 2.4: Sensitive Data in Logs
        logger_file = self.project_root / "ghl_real_estate_ai/ghl_utils/logger.py"
        if logger_file.exists():
            content = logger_file.read_text()
            has_masking = "mask" in content.lower() or "redact" in content.lower()
            self.print_check(
                "Log Data Masking",
                has_masking,
                "PII masking in logs" if has_masking else "No masking detected"
            )

            if not has_masking:
                self.log_finding(
                    "medium",
                    "Data Protection",
                    "PII in Logs Risk",
                    "No PII masking detected in logging configuration",
                    "Implement log masking for sensitive fields (email, phone, etc.)",
                    ["GDPR Article 25", "CCPA"]
                )

        # Check 2.5: Backup Encryption
        # This would typically check backup scripts or configurations
        self.print_check(
            "Backup Encryption Policy",
            False,  # Assume not implemented unless proven
            "Manual verification required"
        )
        self.log_finding(
            "info",
            "Data Protection",
            "Verify Backup Encryption",
            "Manual verification needed for backup encryption",
            "Ensure all backups are encrypted at rest and in transit"
        )

    # ========================================================================
    # 3. API Security Hardening Validation
    # ========================================================================

    def validate_api_security(self):
        """Validate API security hardening."""
        self.print_section("3. API SECURITY HARDENING")

        # Check 3.1: Rate Limiting
        middleware_path = self.project_root / "ghl_real_estate_ai/api/middleware"
        has_rate_limiting = False
        if middleware_path.exists():
            for middleware_file in middleware_path.glob("*.py"):
                content = middleware_file.read_text()
                if "rate_limit" in content.lower():
                    has_rate_limiting = True
                    break

        self.print_check(
            "API Rate Limiting Middleware",
            has_rate_limiting,
            "Rate limiting implemented"
        )

        if not has_rate_limiting:
            self.log_finding(
                "high",
                "API Security",
                "Missing Rate Limiting",
                "No rate limiting middleware detected",
                "Implement Redis-backed rate limiting",
                ["OWASP API4:2023"]
            )

        # Check 3.2: Input Validation
        has_pydantic = False
        api_routes = self.project_root / "ghl_real_estate_ai/api/routes"
        if api_routes.exists():
            for route_file in api_routes.glob("*.py"):
                content = route_file.read_text()
                if "BaseModel" in content or "pydantic" in content:
                    has_pydantic = True
                    break

        self.print_check(
            "Input Validation (Pydantic)",
            has_pydantic,
            "Pydantic models for validation"
        )

        # Check 3.3: SQL Injection Protection
        # Check for ORM usage (SQLAlchemy) vs raw SQL
        uses_orm = False
        project_files = list(self.project_root.glob("**/*.py"))
        for file in project_files[:100]:  # Sample first 100 files
            try:
                if "sqlalchemy" in file.read_text().lower():
                    uses_orm = True
                    break
            except Exception:
                continue

        self.print_check(
            "SQL Injection Protection (ORM)",
            uses_orm,
            "SQLAlchemy ORM detected" if uses_orm else "Manual SQL verification needed"
        )

        # Check 3.4: CORS Configuration
        main_api_file = self.project_root / "ghl_real_estate_ai/api/main.py"
        if main_api_file.exists():
            content = main_api_file.read_text()
            has_cors_config = "CORSMiddleware" in content
            has_origin_restriction = "allow_origins" in content and "localhost" not in content.lower()

            self.print_check(
                "CORS Configuration",
                has_cors_config,
                "CORS middleware configured"
            )

            self.print_check(
                "CORS Origin Restriction",
                has_origin_restriction,
                "Restricted origins in production" if has_origin_restriction else "May allow localhost in production"
            )

            if not has_origin_restriction:
                self.log_finding(
                    "medium",
                    "API Security",
                    "Permissive CORS Configuration",
                    "CORS may allow localhost or overly permissive origins",
                    "Restrict CORS origins to production ontario_millss only",
                    ["OWASP A05:2021"]
                )

        # Check 3.5: Security Headers
        has_security_headers = False
        if middleware_path.exists():
            for middleware_file in middleware_path.glob("*.py"):
                content = middleware_file.read_text()
                if "X-Content-Type-Options" in content or "SecurityHeadersMiddleware" in content:
                    has_security_headers = True
                    break

        self.print_check(
            "Security Headers Middleware",
            has_security_headers,
            "Security headers configured"
        )

        if not has_security_headers:
            self.log_finding(
                "medium",
                "API Security",
                "Missing Security Headers",
                "Security headers middleware not detected",
                "Implement security headers (CSP, X-Frame-Options, etc.)",
                ["OWASP A05:2021"]
            )

        # Check 3.6: Webhook Signature Verification
        webhook_file = self.project_root / "ghl_real_estate_ai/api/routes/webhook.py"
        if webhook_file.exists():
            content = webhook_file.read_text()
            has_signature_verify = "signature" in content.lower() and "verify" in content.lower()

            self.print_check(
                "Webhook Signature Verification",
                has_signature_verify,
                "Signature verification implemented"
            )

            if not has_signature_verify:
                self.log_finding(
                    "critical",
                    "API Security",
                    "Missing Webhook Signature Verification",
                    "Webhooks may not verify signatures from external providers",
                    "Implement HMAC signature verification for all webhooks",
                    ["OWASP API2:2023"]
                )

    # ========================================================================
    # 4. Infrastructure Security Validation
    # ========================================================================

    def validate_infrastructure_security(self):
        """Validate infrastructure security."""
        self.print_section("4. INFRASTRUCTURE SECURITY")

        # Check 4.1: HTTPS Enforcement
        main_api_file = self.project_root / "ghl_real_estate_ai/api/main.py"
        if main_api_file.exists():
            content = main_api_file.read_text()
            has_https_redirect = "HTTPSRedirectMiddleware" in content

            self.print_check(
                "HTTPS Enforcement",
                has_https_redirect,
                "HTTPS redirect middleware configured"
            )
        else:
            self.print_check("HTTPS Enforcement", False, "main.py not found")

        # Check 4.2: Secrets Management
        env_files_in_repo = list(self.project_root.glob(".env*"))
        env_files_in_repo = [f for f in env_files_in_repo if not f.name.endswith('.template') and not f.name.endswith('.example')]

        has_secret_exposure = len(env_files_in_repo) > 0
        self.print_check(
            "Secrets Not in Repository",
            not has_secret_exposure,
            f"Found {len(env_files_in_repo)} .env files" if has_secret_exposure else "No .env files in repo"
        )

        if has_secret_exposure:
            self.log_finding(
                "critical",
                "Infrastructure Security",
                "Secrets in Repository",
                f"Found {len(env_files_in_repo)} .env files that may contain secrets",
                "Remove .env files from repository and add to .gitignore",
                ["OWASP A02:2021", "PCI DSS 6.3.1"]
            )

        # Check 4.3: Dependency Vulnerabilities (if safety is installed)
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                packages = json.loads(result.stdout)
                package_count = len(packages)
                self.print_check(
                    "Dependency Inventory",
                    True,
                    f"{package_count} packages installed"
                )

                # Check for known vulnerable packages (simple check)
                vulnerable_packages = []
                for pkg in packages:
                    # This is a simplified check - use proper vulnerability scanning
                    if pkg['version'].startswith('0.'):
                        vulnerable_packages.append(pkg['name'])

                if vulnerable_packages:
                    self.log_finding(
                        "info",
                        "Infrastructure Security",
                        "Pre-1.0 Dependencies Detected",
                        f"Found {len(vulnerable_packages)} packages with version < 1.0",
                        "Review pre-1.0 dependencies for security posture"
                    )
        except Exception as e:
            self.print_check("Dependency Analysis", False, f"Error: {str(e)}")

        # Check 4.4: Docker Security (if Dockerfile exists)
        dockerfile = self.project_root / "Dockerfile"
        if dockerfile.exists():
            content = dockerfile.read_text()

            # Check for non-root user
            uses_nonroot = "USER" in content and "root" not in content.lower()
            self.print_check(
                "Docker Non-Root User",
                uses_nonroot,
                "Non-root user configured" if uses_nonroot else "May run as root"
            )

            if not uses_nonroot:
                self.log_finding(
                    "medium",
                    "Infrastructure Security",
                    "Docker Running as Root",
                    "Dockerfile may not configure non-root user",
                    "Add USER directive to run container as non-root",
                    ["CIS Docker Benchmark"]
                )

            # Check for multi-stage build
            is_multistage = content.count("FROM") > 1
            self.print_check(
                "Docker Multi-Stage Build",
                is_multistage,
                "Multi-stage build reduces attack surface"
            )
        else:
            self.print_check("Docker Configuration", False, "Dockerfile not found")

        # Check 4.5: Logging Configuration
        logger_file = self.project_root / "ghl_real_estate_ai/ghl_utils/logger.py"
        if logger_file.exists():
            content = logger_file.read_text()
            has_structured_logging = "json" in content.lower() or "structured" in content.lower()

            self.print_check(
                "Structured Logging",
                has_structured_logging,
                "JSON/structured logging for SIEM integration"
            )
        else:
            self.print_check("Logging Configuration", False, "logger.py not found")

    # ========================================================================
    # 5. Compliance & Auditing Validation
    # ========================================================================

    def validate_compliance(self):
        """Validate compliance and auditing controls."""
        self.print_section("5. COMPLIANCE & AUDITING")

        # Check 5.1: Audit Logging
        audit_logger_file = self.project_root / "ghl_real_estate_ai/security/audit_logger.py"
        has_audit_logging = audit_logger_file.exists()

        self.print_check(
            "Audit Logging Framework",
            has_audit_logging,
            "Dedicated audit logger exists" if has_audit_logging else "No audit logger found"
        )

        if not has_audit_logging:
            self.log_finding(
                "high",
                "Compliance",
                "Missing Audit Logging",
                "No dedicated audit logging framework detected",
                "Implement comprehensive audit logging for security events",
                ["GDPR Article 30", "HIPAA 164.308(a)(1)(ii)(D)", "SOC2 CC7.2"]
            )

        # Check 5.2: Data Retention Policies
        # This would typically check configuration files
        self.print_check(
            "Data Retention Policy",
            False,  # Assume not implemented unless proven
            "Manual verification required"
        )

        self.log_finding(
            "info",
            "Compliance",
            "Verify Data Retention Policies",
            "Manual verification needed for data retention policies",
            "Document and implement data retention policies per compliance requirements"
        )

        # Check 5.3: GDPR Compliance Readiness
        # Check for consent management, right to erasure, etc.
        gdpr_indicators = 0

        project_files = list(self.project_root.glob("**/*.py"))
        for file in project_files[:100]:  # Sample
            try:
                content = file.read_text().lower()
                if "consent" in content:
                    gdpr_indicators += 1
                if "right to erasure" in content or "delete_user" in content:
                    gdpr_indicators += 1
                if "data export" in content:
                    gdpr_indicators += 1
            except Exception:
                continue

        self.print_check(
            "GDPR Compliance Indicators",
            gdpr_indicators >= 2,
            f"Found {gdpr_indicators} GDPR-related implementations"
        )

        # Check 5.4: Access Control Logging
        has_access_logging = False
        if audit_logger_file.exists():
            content = audit_logger_file.read_text()
            has_access_logging = "access" in content.lower() or "authorization" in content.lower()

        self.print_check(
            "Access Control Audit Logging",
            has_access_logging,
            "Access events logged" if has_access_logging else ""
        )

        # Check 5.5: Incident Response Documentation
        incident_response_docs = list(self.project_root.glob("**/INCIDENT_RESPONSE*.md"))
        has_ir_plan = len(incident_response_docs) > 0

        self.print_check(
            "Incident Response Plan",
            has_ir_plan,
            f"Found {len(incident_response_docs)} IR documents" if has_ir_plan else "No IR plan found"
        )

        if not has_ir_plan:
            self.log_finding(
                "medium",
                "Compliance",
                "Missing Incident Response Plan",
                "No incident response documentation found",
                "Create incident response plan with roles, procedures, and contacts",
                ["SOC2 CC7.4", "ISO 27001 A.16"]
            )

    # ========================================================================
    # Report Generation
    # ========================================================================

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security validation report."""

        total_findings = sum(len(findings) for findings in self.findings.values())

        # Calculate risk score (0-100, lower is better)
        risk_score = (
            len(self.findings["critical"]) * 25 +
            len(self.findings["high"]) * 10 +
            len(self.findings["medium"]) * 5 +
            len(self.findings["low"]) * 2
        )
        risk_score = min(100, risk_score)

        # Determine overall status
        if len(self.findings["critical"]) > 0:
            status = "CRITICAL - Immediate Action Required"
            status_color = Colors.FAIL
        elif len(self.findings["high"]) > 3:
            status = "HIGH RISK - Action Required"
            status_color = Colors.WARNING
        elif len(self.findings["high"]) > 0 or len(self.findings["medium"]) > 5:
            status = "MEDIUM RISK - Improvements Needed"
            status_color = Colors.WARNING
        else:
            status = "LOW RISK - Good Security Posture"
            status_color = Colors.OKGREEN

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "project": "Jorge's Revenue Acceleration Platform",
            "validation_summary": {
                "total_checks": self.total_checks,
                "passed_checks": self.passed_checks,
                "failed_checks": self.total_checks - self.passed_checks,
                "pass_rate": f"{(self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0:.1f}%"
            },
            "findings_summary": {
                "critical": len(self.findings["critical"]),
                "high": len(self.findings["high"]),
                "medium": len(self.findings["medium"]),
                "low": len(self.findings["low"]),
                "info": len(self.findings["info"]),
                "total": total_findings
            },
            "risk_score": risk_score,
            "status": status,
            "findings": self.findings,
            "compliance_assessment": self.assess_compliance(),
            "recommendations": self.generate_recommendations()
        }

        # Print summary
        self.print_section("SECURITY VALIDATION SUMMARY")

        print(f"{Colors.BOLD}Overall Status:{Colors.ENDC} {status_color}{status}{Colors.ENDC}")
        print(f"{Colors.BOLD}Risk Score:{Colors.ENDC} {risk_score}/100 (lower is better)\n")

        print(f"{Colors.BOLD}Checks Performed:{Colors.ENDC}")
        print(f"  Total Checks: {self.total_checks}")
        print(f"  {Colors.OKGREEN}Passed: {self.passed_checks}{Colors.ENDC}")
        print(f"  {Colors.FAIL}Failed: {self.total_checks - self.passed_checks}{Colors.ENDC}")
        print(f"  Pass Rate: {(self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0:.1f}%\n")

        print(f"{Colors.BOLD}Security Findings:{Colors.ENDC}")
        if len(self.findings["critical"]) > 0:
            print(f"  {Colors.FAIL}Critical: {len(self.findings['critical'])}{Colors.ENDC}")
        if len(self.findings["high"]) > 0:
            print(f"  {Colors.WARNING}High: {len(self.findings['high'])}{Colors.ENDC}")
        if len(self.findings["medium"]) > 0:
            print(f"  {Colors.WARNING}Medium: {len(self.findings['medium'])}{Colors.ENDC}")
        if len(self.findings["low"]) > 0:
            print(f"  {Colors.OKCYAN}Low: {len(self.findings['low'])}{Colors.ENDC}")
        if len(self.findings["info"]) > 0:
            print(f"  {Colors.OKBLUE}Info: {len(self.findings['info'])}{Colors.ENDC}")

        if total_findings == 0:
            print(f"  {Colors.OKGREEN}No security findings - excellent!{Colors.ENDC}")

        return report

    def assess_compliance(self) -> Dict[str, str]:
        """Assess compliance readiness for various standards."""
        compliance = {}

        # OWASP Top 10
        owasp_findings = sum(
            1 for severity in self.findings.values()
            for finding in severity
            if any("OWASP" in impact for impact in finding.get("compliance_impact", []))
        )
        compliance["OWASP Top 10"] = "Compliant" if owasp_findings == 0 else f"{owasp_findings} issues found"

        # GDPR
        gdpr_findings = sum(
            1 for severity in self.findings.values()
            for finding in severity
            if any("GDPR" in impact for impact in finding.get("compliance_impact", []))
        )
        compliance["GDPR"] = "Ready" if gdpr_findings == 0 else f"{gdpr_findings} gaps identified"

        # PCI DSS
        pci_findings = sum(
            1 for severity in self.findings.values()
            for finding in severity
            if any("PCI" in impact for impact in finding.get("compliance_impact", []))
        )
        compliance["PCI DSS"] = "Compliant" if pci_findings == 0 else f"{pci_findings} requirements not met"

        # SOC2
        soc2_findings = sum(
            1 for severity in self.findings.values()
            for finding in severity
            if any("SOC2" in impact for impact in finding.get("compliance_impact", []))
        )
        compliance["SOC2"] = "Ready" if soc2_findings == 0 else f"{soc2_findings} controls needed"

        return compliance

    def generate_recommendations(self) -> List[str]:
        """Generate top recommendations based on findings."""
        recommendations = []

        # Critical findings
        if len(self.findings["critical"]) > 0:
            recommendations.append(
                f"URGENT: Address {len(self.findings['critical'])} critical security issues immediately"
            )

        # High findings
        if len(self.findings["high"]) > 0:
            recommendations.append(
                f"HIGH PRIORITY: Resolve {len(self.findings['high'])} high-risk vulnerabilities"
            )

        # Specific recommendations based on common patterns
        categories = {}
        for severity in ["critical", "high", "medium"]:
            for finding in self.findings[severity]:
                cat = finding["category"]
                categories[cat] = categories.get(cat, 0) + 1

        # Add category-specific recommendations
        if categories.get("Authentication", 0) > 2:
            recommendations.append(
                "Strengthen authentication framework - multiple issues detected"
            )

        if categories.get("Data Protection", 0) > 2:
            recommendations.append(
                "Enhance data protection measures - encryption and privacy concerns"
            )

        if categories.get("API Security", 0) > 2:
            recommendations.append(
                "Harden API security - implement rate limiting and input validation"
            )

        if categories.get("Compliance", 0) > 2:
            recommendations.append(
                "Improve compliance readiness - audit logging and documentation needed"
            )

        # General recommendations
        if not recommendations:
            recommendations.append(
                "Maintain current security posture with regular audits"
            )
            recommendations.append(
                "Implement automated security testing in CI/CD pipeline"
            )

        return recommendations

    def save_report(self, filename: str = None):
        """Save report to JSON file."""
        if not filename:
            filename = f"security_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        report = self.generate_report()

        output_path = self.project_root / filename
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n{Colors.OKGREEN}Report saved to: {output_path}{Colors.ENDC}")

        # Also save a summary markdown
        md_filename = filename.replace('.json', '.md')
        self.save_markdown_summary(md_filename, report)

    def save_markdown_summary(self, filename: str, report: Dict[str, Any]):
        """Save a human-readable markdown summary."""
        output_path = self.project_root / filename

        with open(output_path, 'w') as f:
            f.write("# Enterprise Security Validation Report\n\n")
            f.write(f"**Generated:** {report['timestamp']}\n\n")
            f.write(f"**Project:** {report['project']}\n\n")

            f.write("## Overall Status\n\n")
            f.write(f"**Status:** {report['status']}\n\n")
            f.write(f"**Risk Score:** {report['risk_score']}/100\n\n")

            f.write("## Validation Summary\n\n")
            summary = report['validation_summary']
            f.write(f"- Total Checks: {summary['total_checks']}\n")
            f.write(f"- Passed: {summary['passed_checks']}\n")
            f.write(f"- Failed: {summary['failed_checks']}\n")
            f.write(f"- Pass Rate: {summary['pass_rate']}\n\n")

            f.write("## Findings Summary\n\n")
            findings_summary = report['findings_summary']
            f.write(f"- 🔴 Critical: {findings_summary['critical']}\n")
            f.write(f"- 🟠 High: {findings_summary['high']}\n")
            f.write(f"- 🟡 Medium: {findings_summary['medium']}\n")
            f.write(f"- 🔵 Low: {findings_summary['low']}\n")
            f.write(f"- ℹ️ Info: {findings_summary['info']}\n\n")

            f.write("## Compliance Assessment\n\n")
            for standard, status in report['compliance_assessment'].items():
                f.write(f"- **{standard}:** {status}\n")
            f.write("\n")

            f.write("## Top Recommendations\n\n")
            for i, rec in enumerate(report['recommendations'], 1):
                f.write(f"{i}. {rec}\n")
            f.write("\n")

            # Detailed findings
            for severity in ["critical", "high", "medium", "low", "info"]:
                findings = report['findings'][severity]
                if findings:
                    f.write(f"## {severity.upper()} Findings\n\n")
                    for i, finding in enumerate(findings, 1):
                        f.write(f"### {i}. {finding['title']}\n\n")
                        f.write(f"**Category:** {finding['category']}\n\n")
                        f.write(f"**Description:** {finding['description']}\n\n")
                        if finding.get('remediation'):
                            f.write(f"**Remediation:** {finding['remediation']}\n\n")
                        if finding.get('compliance_impact'):
                            f.write(f"**Compliance Impact:** {', '.join(finding['compliance_impact'])}\n\n")
                        f.write("---\n\n")

        print(f"{Colors.OKGREEN}Summary saved to: {output_path}{Colors.ENDC}")


async def main():
    """Main execution function."""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("="*80)
    print("ENTERPRISE SECURITY VALIDATION")
    print("Jorge's Revenue Acceleration Platform")
    print("="*80)
    print(f"{Colors.ENDC}\n")

    validator = SecurityValidator()

    # Run all validation checks
    validator.validate_authentication()
    validator.validate_data_protection()
    validator.validate_api_security()
    validator.validate_infrastructure_security()
    validator.validate_compliance()

    # Generate and save report
    report = validator.generate_report()
    validator.save_report()

    # Print final recommendations
    print(f"\n{Colors.HEADER}{Colors.BOLD}TOP RECOMMENDATIONS:{Colors.ENDC}")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")

    print(f"\n{Colors.OKGREEN}✓ Security validation complete!{Colors.ENDC}\n")

    # Exit with error code if critical issues found
    if len(validator.findings["critical"]) > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
